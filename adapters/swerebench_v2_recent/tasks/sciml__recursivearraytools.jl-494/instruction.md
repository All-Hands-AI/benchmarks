Views of `VectorOfArray` with differently sized vectors gives wrong result
**Describe the bug 🐞**

Creating a view of a `VectorOfArray` with inner vectors, which have different lengths does not return the expected slice.

**Expected behavior**

It should return the same slice as the corresponding slice without using a view. 

**Minimal Reproducible Example 👇**

```julia
julia> f = VectorOfArray([[1.0], [2.0, 3.0]])
VectorOfArray{Float64,2}:
2-element Vector{Vector{Float64}}:
 [1.0]
 [2.0, 3.0]

julia> f[:, 1]
1-element Vector{Float64}:
 1.0

julia> view(f, :, 1)
1-element view(::VectorOfArray{Float64, 2, Vector{Vector{Float64}}}, :, 1) with eltype Float64:
 1.0

julia> f[:, 2]
2-element Vector{Float64}:
 2.0
 3.0

julia> view(f, :, 2) # Here, I would expect the view on [2.0, 3.0]
1-element view(::VectorOfArray{Float64, 2, Vector{Vector{Float64}}}, :, 2) with eltype Float64:
 2.0
```

Similarly:
```julia
julia> f2 = VectorOfArray([[1.0, 2.0], [3.0]])
VectorOfArray{Float64,2}:
2-element Vector{Vector{Float64}}:
 [1.0, 2.0]
 [3.0]

julia> f2[:, 1]
2-element Vector{Float64}:
 1.0
 2.0

julia> f2[:, 2]
1-element Vector{Float64}:
 3.0

julia> view(f2, :, 1)
2-element view(::VectorOfArray{Float64, 2, Vector{Vector{Float64}}}, :, 1) with eltype Float64:
 1.0
 2.0

julia> view(f2, :, 2) # There should be no `#undef` here
2-element view(::VectorOfArray{Float64, 2, Vector{Vector{Float64}}}, :, 2) with eltype Float64:
   3.0
 #undef
```

**Error & Stacktrace ⚠️**

No error, but wrong result. See above.

**Environment (please complete the following information):**

  - Output of `using Pkg; Pkg.status()`

```julia
Status `/tmp/jl_U8APBX/Project.toml`
  [731186ca] RecursiveArrayTools v3.33.0
```

  - Output of `using Pkg; Pkg.status(; mode = PKGMODE_MANIFEST)`

```julia
Status `/tmp/jl_U8APBX/Manifest.toml`
  [7d9f7c33] Accessors v0.1.42
  [79e6a3ab] Adapt v4.3.0
  [4fba245c] ArrayInterface v7.19.0
  [a33af91c] CompositionsBase v0.1.2
  [187b0558] ConstructionBase v1.5.8
  [a8cc5b0e] Crayons v4.1.1
  [9a962f9c] DataAPI v1.16.0
  [e2d170a0] DataValueInterfaces v1.0.0
  [ffbed154] DocStringExtensions v0.9.4
  [e2ba6199] ExprTools v0.1.10
  [46192b85] GPUArraysCore v0.2.0
  [3587e190] InverseFunctions v0.1.17
  [82899510] IteratorInterfaceExtensions v1.0.0
  [b964fa9f] LaTeXStrings v1.4.0
  [1914dd2f] MacroTools v0.5.16
  [bac558e1] OrderedCollections v1.8.1
⌅ [aea7be01] PrecompileTools v1.2.1
  [21216c6a] Preferences v1.4.3
  [08abe8d2] PrettyTables v2.4.0
  [3cdcf5f2] RecipesBase v1.3.4
  [731186ca] RecursiveArrayTools v3.33.0
  [189a3867] Reexport v1.2.2
  [ae029012] Requires v1.3.1
  [7e49a35a] RuntimeGeneratedFunctions v0.5.15
  [1e83bf80] StaticArraysCore v1.4.3
  [10745b16] Statistics v1.11.1
  [892a3eda] StringManipulation v0.4.1
  [2efcf032] SymbolicIndexingInterface v0.3.40
  [3783bdb8] TableTraits v1.0.1
  [bd369af6] Tables v1.12.0
  [56f22d72] Artifacts v1.11.0
  [2a0f44e3] Base64 v1.11.0
  [ade2ca70] Dates v1.11.0
  [8f399da3] Libdl v1.11.0
  [37e2e46d] LinearAlgebra v1.11.0
  [d6f4376e] Markdown v1.11.0
  [de0858da] Printf v1.11.0
  [9a3f8284] Random v1.11.0
  [ea8e919c] SHA v0.7.0
  [9e88b42a] Serialization v1.11.0
  [fa267f1f] TOML v1.0.3
  [cf7118a7] UUIDs v1.11.0
  [4ec0a83e] Unicode v1.11.0
  [e66e0078] CompilerSupportLibraries_jll v1.1.1+0
  [4536629a] OpenBLAS_jll v0.3.27+1
  [8e850b90] libblastrampoline_jll v5.11.0+0
```

  - Output of `versioninfo()`

```julia
Julia Version 1.11.5
Commit 760b2e5b739 (2025-04-14 06:53 UTC)
Build Info:
  Official https://julialang.org/ release
Platform Info:
  OS: Linux (x86_64-linux-gnu)
  CPU: 12 × 13th Gen Intel(R) Core(TM) i5-1345U
  WORD_SIZE: 64
  LLVM: libLLVM-16.0.6 (ORCJIT, goldmont)
Threads: 1 default, 0 interactive, 1 GC (on 12 virtual cores)
```

**Additional context**

Add any other context about the problem here.

Relevant interfaces:
Function: view(A::AbstractVectorOfArray, I::Vararg{Any, M}) where {M}
Location: src/vector_of_array.jl (adds special handling for heterogeneous column views)
Inputs: 
- A: an AbstractVectorOfArray whose elements are vectors that may have different lengths.  
- I: a variable‑length tuple of indexing arguments; for the heterogeneous case the pattern must be `(:, col)` where the first index is `Colon()` and the second index is an `Int` specifying the column to view. Additional indexing forms are forwarded to the generic `to_indices` logic.
Outputs: 
- Returns a `SubArray` that views the specified column of `A`. The length of the view matches the actual length of the inner vector at that column. A `BoundsError` is thrown if the column index is out of range.
Description: Introduces a specialized `Base.view` method for `VectorOfArray` to correctly handle slicing when inner vectors have differing sizes. The view behaves like a regular column slice, supports `collect`, element mutation, and propagates changes back to the parent array, fixing issue #453.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

