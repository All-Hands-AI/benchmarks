`invariant failed` error

## Required: Configuration ##

`.scalafmt.conf`

```
version = "3.10.1"
runner.dialect = scala213
```


## Required: Command-line parameters ##

```
$ scala --version           
Scala code runner version: 1.9.0
Scala version (default): 3.7.3
```



## Steps

```scala
trait A {
  def b(
     x: Int => List[
       Int
     ]*
  ): Int = 2
}
```

`scala fmt A.scala`


## Problem

```
org.scalafmt.cli.FailedToFormat: /Users/kenji/scalafmt-invariant-failed-err/A.scala

Caused by: org.scalameta.invariants.InvariantFailedException: invariant failed:
when verifying parentCheckOk.&&(org.scalameta.`package`.debug(this, parentPrefix, destination))
found that parentCheckOk is false
where TypeRepeatedImpl = List[
       Int
     ]*
where destination = res
where parentCheckOk = false
where parentPrefix = Type.Function
where this = List[
       Int
     ]*

	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
	at scala.scalanative.runtime.StackTrace$.materializeStackTrace(Unknown Source)
```

## Expectation


## Workaround

use scalafmt 3.10.0

## Notes

Relevant interfaces:
Method: ScalametaParser.expr(location: Location, allowRepeated: Boolean) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- location: indicates where the parsed term will appear (e.g., NoStat, BlockStat, TemplateStat). 
- allowRepeated: Boolean flag that enables parsing of repeated arguments (`_*`). When false repeated arguments are rejected with a syntax error.
Outputs: Returns a parsed Term. Throws ParseException if the input is syntactically invalid, for example when a repeated argument appears in a disallowed position.
Description: Parses a term according to the given location, optionally allowing repeated arguments. Used by the test suite via the helper `term(...)` to verify that disallowed repeated arguments now raise a ParseException.

Method: ScalametaParser.exprOtherRest(startPos: Int, prefix: Term, location: Location, allowRepeated: Boolean) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- startPos: start offset of the expression in the source. 
- prefix: the already‑parsed left‑hand side term. 
- location: context where the expression appears. 
- allowRepeated: Boolean controlling whether `_*` may be parsed.
Outputs: Returns a Term representing the rest of the expression after the prefix. May raise a syntax error if a repeated argument is encountered while `allowRepeated` is false.
Description: Continues parsing after an initial term, handling assignments, type ascriptions, and repeated arguments. The new flag propagates the “no repeated args” rule that the tests assert.

Method: ScalametaParser.postfixExpr(allowRepeated: Boolean) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean that determines whether a trailing `_*` is accepted in a postfix expression.
Outputs: Returns a Term representing the parsed postfix expression. Throws a ParseException when a repeated argument is found and `allowRepeated` is false.
Description: Parses postfix operator chains. The added flag ensures constructs like `a + b: _*` now fail, matching the expectations in the updated tests.

Method: ScalametaParser.prefixExpr(allowRepeated: Boolean) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean controlling acceptance of repeated arguments after a prefix expression.
Outputs: Returns a Term for the parsed prefix expression, or propagates a syntax error for disallowed repeated arguments.
Description: Handles unary operators and the start of simple expressions. The flag is used internally when parsing terms such as `a + (bs: _*) * c`, which the tests now expect to reject.

Method: ScalametaParser.simpleExpr(allowRepeated: Boolean) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean that enables parsing of repeated arguments inside simple expressions (e.g., argument lists).
Outputs: Returns a Term for the simple expression. May raise ParseException if a repeated argument appears where `allowRepeated` is false.
Description: Parses the core of an expression (identifiers, literals, parenthesised terms, etc.). The new flag propagates the “no repeated args” rule into contexts exercised by the test suite.

Method: ScalametaParser.blockStatSeq(allowRepeated: Boolean = false) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean indicating whether a statement block may contain a `Term.Repeated`. Default is false.
Outputs: Returns a List[Stat] representing the statements in a block. If `allowRepeated` is true it validates that at most one statement is a repeated argument; otherwise it raises a syntax error.
Description: Parses a sequence of statements inside `{ ... }` or an indentation block. The test suite indirectly validates that repeated arguments are rejected inside ordinary blocks, while they are still allowed in allowed‑repeated contexts.

Function: blockRaw(allowRepeated: Boolean = false) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean flag forwarded to blockStatSeq.
Outputs: Returns a Term.Block containing the parsed block statements.
Description: Constructs a raw block term. The flag ensures that blocks produced by the parser respect the new “no repeated args” rule.

Function: blockOnBrace(allowRepeated: Boolean = false) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean forwarded to blockStatSeq.
Outputs: Returns a Term representing a brace‑delimited block.
Description: Parses `{ ... }` blocks, propagating the repeated‑argument restriction needed for the updated tests.

Function: blockExprOnBrace(allowRepeated: Boolean = false, isOptional: Boolean = false) 
Location: scalameta/parsers/shared/src/main/scala/scala/meta/internal/parsers/ScalametaParser.scala
Inputs: 
- allowRepeated: Boolean that permits repeated arguments inside the brace block when true. 
- isOptional: indicates whether the brace block is optional (used for empty blocks).
Outputs: Returns a Term for the brace block expression.
Description: Handles expression‑level brace blocks, now checking the repeated‑argument rule as exercised by the test suite.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

