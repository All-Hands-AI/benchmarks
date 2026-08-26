fix: Ignoring a lint warning only works with the ignore aligned at the start of the line
**Description**
I am using `@visibleForTesting` for a couple of public methods in my bloc. And therefore would like to ignore the lint warning.
However, when using `// ignore: avoid_public_bloc_methods`, it only works when this line is aligned at the start.
The dart formatter always aligns this ignore with two spaces at the start. So it always shows the warning.
Other lints from Dart itself work as expected.

Not aligned at the start:
![Image](https://github.com/user-attachments/assets/48365ab6-2be3-45c1-a60d-ebe4cec16718)

Aligned at the start:
![Image](https://github.com/user-attachments/assets/9db4d454-aa5e-4b7e-90a3-d0f47e9f3f9c)

**Expected Behavior**
I expect the lint ignore to work with leading spaces as well.

Relevant interfaces:
No new interfaces are introduced.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

