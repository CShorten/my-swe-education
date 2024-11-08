# RAFT Consensus Algorithm
## A Detailed Technical Guide

## 1. Introduction to RAFT

RAFT (Reliable, Replicated, Redundant, And Fault-Tolerant) is a consensus algorithm designed to be more understandable than Paxos while providing the same guarantees. It manages a replicated log of operations across a cluster of machines to maintain consistency.

### 1.1 Key Properties
- Strong leader
- Leader election
- Membership changes
- Log replication
- Safety guarantees

## 2. Server States

Each server in a RAFT cluster can be in one of three states:
```plaintext
                  ┌─────────────┐
                  │   Follower  │
                  └──────┬──────┘
                         │ 
                    Election timeout
                         │ 
                  ┌─────▼──────┐
              ┌──│  Candidate  │──┐
   Discovers  │  └─────┬──────┘  │  Receives votes
   current    │        │         │  from majority
   leader     │   Starts        │
              │   election      │
              │        │         │
              │  ┌─────▼──────┐  │
              └─►│   Leader    │◄─┘
                 └────────────┘
```

### 2.1 State Implementation

```go
type RaftState int

const (
    Follower RaftState = iota
    Candidate
    Leader
)

type RaftServer struct {
    // Persistent state
    currentTerm int
    votedFor    int
    log         []LogEntry
    
    // Volatile state
    state       RaftState
    commitIndex int
    lastApplied int
    
    // Leader volatile state
    nextIndex   []int
    matchIndex  []int
    
    // Timing
    electionTimeout  time.Duration
    heartbeatTimeout time.Duration
}
```

## 3. Leader Election

### 3.1 Election Process
```go
func (s *RaftServer) startElection() {
    s.state = Candidate
    s.currentTerm++
    s.votedFor = s.id
    
    // Prepare RequestVote RPCs
    args := RequestVoteArgs{
        Term:         s.currentTerm,
        CandidateId:  s.id,
        LastLogIndex: len(s.log) - 1,
        LastLogTerm:  s.log[len(s.log)-1].Term,
    }
    
    // Send RequestVote RPCs to all other servers
    votes := 1  // Vote for self
    for _, peer := range s.peers {
        go func(peer Peer) {
            response := peer.RequestVote(args)
            if response.VoteGranted {
                votes++
                if votes > len(s.peers)/2 {
                    s.becomeLeader()
                }
            }
        }(peer)
    }
}
```

### 3.2 Vote Request Handler
```go
func (s *RaftServer) handleRequestVote(args RequestVoteArgs) RequestVoteResponse {
    if args.Term < s.currentTerm {
        return RequestVoteResponse{
            Term:        s.currentTerm,
            VoteGranted: false,
        }
    }
    
    if s.votedFor == -1 || s.votedFor == args.CandidateId {
        if s.isLogUpToDate(args.LastLogIndex, args.LastLogTerm) {
            s.votedFor = args.CandidateId
            return RequestVoteResponse{
                Term:        s.currentTerm,
                VoteGranted: true,
            }
        }
    }
    
    return RequestVoteResponse{
        Term:        s.currentTerm,
        VoteGranted: false,
    }
}
```

## 4. Log Replication

### 4.1 Log Structure
```go
type LogEntry struct {
    Term    int
    Index   int
    Command interface{}
}

type AppendEntriesArgs struct {
    Term         int
    LeaderId     int
    PrevLogIndex int
    PrevLogTerm  int
    Entries      []LogEntry
    LeaderCommit int
}

type AppendEntriesResponse struct {
    Term    int
    Success bool
}
```

### 4.2 Log Replication Process
```go
func (s *RaftServer) replicateLog(peer Peer) {
    nextIndex := s.nextIndex[peer.Id]
    
    entries := s.log[nextIndex:]
    args := AppendEntriesArgs{
        Term:         s.currentTerm,
        LeaderId:     s.id,
        PrevLogIndex: nextIndex - 1,
        PrevLogTerm:  s.log[nextIndex-1].Term,
        Entries:      entries,
        LeaderCommit: s.commitIndex,
    }
    
    response := peer.AppendEntries(args)
    
    if response.Success {
        s.matchIndex[peer.Id] = nextIndex + len(entries) - 1
        s.nextIndex[peer.Id] = s.matchIndex[peer.Id] + 1
        s.updateCommitIndex()
    } else {
        // Decrement nextIndex and try again
        s.nextIndex[peer.Id]--
    }
}
```

### 4.3 Append Entries Handler
```go
func (s *RaftServer) handleAppendEntries(args AppendEntriesArgs) AppendEntriesResponse {
    if args.Term < s.currentTerm {
        return AppendEntriesResponse{
            Term:    s.currentTerm,
            Success: false,
        }
    }
    
    // Reset election timeout
    s.resetElectionTimer()
    
    // Check previous log entry
    if args.PrevLogIndex > len(s.log)-1 ||
       s.log[args.PrevLogIndex].Term != args.PrevLogTerm {
        return AppendEntriesResponse{
            Term:    s.currentTerm,
            Success: false,
        }
    }
    
    // Append new entries
    for i, entry := range args.Entries {
        logIndex := args.PrevLogIndex + 1 + i
        if logIndex < len(s.log) {
            if s.log[logIndex].Term != entry.Term {
                s.log = s.log[:logIndex]
                s.log = append(s.log, entry)
            }
        } else {
            s.log = append(s.log, entry)
        }
    }
    
    // Update commit index
    if args.LeaderCommit > s.commitIndex {
        s.commitIndex = min(args.LeaderCommit, len(s.log)-1)
    }
    
    return AppendEntriesResponse{
        Term:    s.currentTerm,
        Success: true,
    }
}
```

## 5. Safety Properties

### 5.1 Election Restriction
```go
func (s *RaftServer) isLogUpToDate(candidateLastIndex, candidateLastTerm int) bool {
    lastIndex := len(s.log) - 1
    lastTerm := s.log[lastIndex].Term
    
    if candidateLastTerm != lastTerm {
        return candidateLastTerm > lastTerm
    }
    return candidateLastIndex >= lastIndex
}
```

### 5.2 Commit Rules
```go
func (s *RaftServer) updateCommitIndex() {
    for n := len(s.log) - 1; n > s.commitIndex; n-- {
        if s.log[n].Term == s.currentTerm {
            // Count replicas including self
            count := 1
            for _, matchIndex := range s.matchIndex {
                if matchIndex >= n {
                    count++
                }
            }
            
            if count > len(s.peers)/2 {
                s.commitIndex = n
                break
            }
        }
    }
}
```

## 6. Configuration Changes

### 6.1 Joint Consensus
```go
type Configuration struct {
    Old []ServerID
    New []ServerID
}

func (s *RaftServer) changeConfiguration(newConfig []ServerID) {
    // Phase 1: Joint consensus
    jointConfig := Configuration{
        Old: s.config,
        New: newConfig,
    }
    s.appendConfigChange(jointConfig)
    
    // Wait for commit
    s.waitForCommit()
    
    // Phase 2: New configuration
    s.appendConfigChange(newConfig)
}
```

## 7. Optimizations

### 7.1 Log Compaction
```go
type Snapshot struct {
    LastIncludedIndex int
    LastIncludedTerm  int
    State            []byte
}

func (s *RaftServer) createSnapshot() {
    if len(s.log) > s.snapshotThreshold {
        state := s.getStateUntil(s.commitIndex)
        s.snapshot = Snapshot{
            LastIncludedIndex: s.commitIndex,
            LastIncludedTerm:  s.log[s.commitIndex].Term,
            State:            state,
        }
        s.log = s.log[s.commitIndex+1:]
    }
}
```

### 7.2 Fast Log Backtracking
```go
type LogMatchIndex struct {
    Index int
    Term  int
}

func (s *RaftServer) findConflictingEntry(prevLogIndex int) int {
    termIndex := make(map[int][]LogMatchIndex)
    
    // Build term -> index mapping
    for i, entry := range s.log {
        termIndex[entry.Term] = append(termIndex[entry.Term], LogMatchIndex{
            Index: i,
            Term:  entry.Term,
        })
    }
    
    // Find last matching term
    for i := prevLogIndex; i >= 0; i-- {
        if matches, exists := termIndex[s.log[i].Term]; exists {
            return matches[0].Index
        }
    }
    
    return 0
}
```

## 8. Implementation Considerations

### 8.1 Timing Parameters
```go
const (
    BaseElectionTimeout  = 150 * time.Millisecond
    ElectionTimeoutJitter = 150 * time.Millisecond
    HeartbeatInterval    = 50 * time.Millisecond
)

func (s *RaftServer) resetElectionTimer() {
    jitter := rand.Int63n(int64(ElectionTimeoutJitter))
    s.electionTimeout = BaseElectionTimeout + time.Duration(jitter)
}
```

### 8.2 State Machine Replication
```go
type StateMachine interface {
    Apply(command interface{}) interface{}
    Snapshot() []byte
    Restore(snapshot []byte)
}

func (s *RaftServer) applyCommitted() {
    for s.lastApplied < s.commitIndex {
        s.lastApplied++
        command := s.log[s.lastApplied].Command
        s.stateMachine.Apply(command)
    }
}
```

## 9. Testing Strategies

### 9.1 Network Partitioning Tests
```go
func TestNetworkPartition(t *testing.T) {
    cluster := NewRaftCluster(5)
    
    // Create partition
    partition1 := cluster.Servers[:2]
    partition2 := cluster.Servers[2:]
    
    // Simulate network partition
    cluster.CreatePartition(partition1, partition2)
    
    // Verify only one leader can be elected
    leaders := cluster.CountLeaders()
    assert.LessOrEqual(t, leaders, 1)
}
```

### 9.2 Leader Failure Tests
```go
func TestLeaderFailure(t *testing.T) {
    cluster := NewRaftCluster(3)
    
    // Wait for leader election
    leader := cluster.WaitForLeader()
    
    // Simulate leader failure
    cluster.CrashServer(leader)
    
    // Verify new leader is elected
    newLeader := cluster.WaitForLeader()
    assert.NotEqual(t, leader, newLeader)
    
    // Verify log consistency
    assert.True(t, cluster.IsLogConsistent())
}
```

## Best Practices

1. **Implementation**
   - Use proper error handling
   - Implement proper logging
   - Handle edge cases carefully
   - Use proper timeouts

2. **Deployment**
   - Use odd number of servers
   - Deploy across failure domains
   - Monitor server health
   - Implement proper backup strategies

3. **Maintenance**
   - Regular health checks
   - Proper monitoring
   - Regular backups
   - Configuration management

4. **Performance**
   - Optimize log compaction
   - Tune timing parameters
   - Monitor network latency
   - Implement proper batching
