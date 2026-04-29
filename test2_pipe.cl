let grade = 88
let passed = yes
func add(a, b) { a + b }
fn double(n) { n + n }
fn square(n) { n * n }
let base = 3
base |> square |> double |> print
let a = 4
let b = 5
a, b |> add |> double |> print
let tag = if (passed == yes) "PASS" else "FAIL"
tag |> print
for 1..6 as k { k |> double |> print }
let result = (grade + 12) * 2
result |> print