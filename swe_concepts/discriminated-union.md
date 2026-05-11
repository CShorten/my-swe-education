A discriminated union (also called a tagged union or sum type) is a value that can be one of several different shapes, with an explicit tag telling you which shape it currently is.
The core idea
Imagine you're modeling "shape" — it can be a circle, rectangle, or triangle, each with different fields:

Circle has a radius
Rectangle has width and height
Triangle has three side lengths

A discriminated union says: this value is exactly one of these, and there's a tag (the "discriminator") that tells you which.
{ type: "circle",    radius: 5 }
{ type: "rectangle", width: 3, height: 4 }
{ type: "triangle",  sides: [3, 4, 5] }
The type field is the discriminator. It tells code reading the value which other fields are meaningful. You'd never have a circle with a width, or a rectangle with a radius.
