Panel not respecting IOverflowable
Given this

```csharp
var markup = new Markup("[yellow]foo[/] [red]pneumonoultramicroscopicsilicovolcanoconiosis[/] [blue]bar qux[/]")
    .Overflow(Overflow.Ellipsis);
var panel = new Panel(markup)
{
    Width = 20,
};

// When
AnsiConsole.Write(panel);
```

I'm seeing

```
┌───────────────────────────────────────────────────────────┐
│ foo pneumonoultramicroscopicsilicovolcanoconiosis bar qux │
└───────────────────────────────────────────────────────────┘
```

Expected
```
┌──────────────────┐
│ foo              │
│ pneumonoultrami… │
│ bar qux          │
└──────────────────┘
```

I have a fix, just want to make sure this is an actual bug or designed behavior with panels

Relevant interfaces:
No new interfaces are introduced.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

