CouldBeSequence and IntelliJ don't agree in chains with groupBy
With 2.0.0-alpha.1, the following is a `CouldBeSequence` violation (it was not in 1.23.8):

```kotlin
fun main() {
    // CouldBeSequence - [groupBy { "test" } could be .asSequence().groupBy { "test" }]
    listOf(1, 2, 3)
        .groupBy { "test" }
        .map { (a, b) -> a to b }
        .filter { (0..1).random() == 1  }
}
```

When you insert the call as instructed, an IntelliJ inspection complains that it's redundant:

<img width="580" height="156" alt="Image" src="https://github.com/user-attachments/assets/bbe2ed25-d1a4-45d5-bef6-1b1b6f07fe10" />

Relevant interfaces:
No new interfaces are introduced.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

