let scores = [45, 78, 92, 38, 65]
let values = [10, 20, 30, 40, 50]
fn triple(n) { n + n + n }
fn square(n) { n * n }
func add(a, b) { a + b }
from scores where n > 60 select n
from values where n > 25 select n * 2
for 1..6 as i { i |> triple |> print }
let limit = 4
while (limit > 1) { limit |> square |> print }
let p = 2
let q = 9
p, q |> add |> square |> print
let bonus = if (p > 1) 10 else 0
bonus |> print