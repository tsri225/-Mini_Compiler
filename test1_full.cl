# INPUT 1: Full Feature Showcase
let name  = "Alice"
let score = 95.5
let age   = 20
let pi    = 3.14159
let x, y  = 6, 7
let active = yes
let debug  = no
let status = if (score > 50) "Pass" else "Fail"
let mood   = if (age > 18) "Adult" else "Minor"
func add(a, b) { a + b }
fn   square(n) { n * n }
fn   double(n) { n + n }
score  |> print
status |> print
x, y   |> add    |> print
x      |> square |> double |> print
for 0..5 as i { i |> print }
let counter = 3
while (counter > 0) { counter |> print }
let nums = [1, 2, 3, 4, 5, 6]
from nums where n > 3 select n * n
let area = pi * square(4)
area |> print