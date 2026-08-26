`nn_name` argument does not work in `SymbolicNeuralNetwork`
I can update the name of the neural network parameter, but not the neural network parameter itself.
```julia
# Preparation
using Lux, ModelingToolkitNeuralNets, StableRNGs, ModelingToolkit
rng = StableRNG(123)
chain = Lux.Chain(
    Lux.Dense(1 => 3, Lux.softplus, use_bias = false),
    Lux.Dense(3 => 3, Lux.softplus, use_bias = false),
    Lux.Dense(3 => 1, Lux.sigmoid_fast, use_bias = false)
)

# Default names.
NN, NN_p = SymbolicNeuralNetwork(; chain, n_input = 1, n_output = 1, rng)
ModelingToolkit.getname(NN) # :nn_name
ModelingToolkit.getname(NN_p) # :p

# Trying to set specific names.
nn_name = :custom_nn_name
nn_p_name = :custom_nn_p_name
NN, NN_p = SymbolicNeuralNetwork(; chain, n_input = 1, n_output = 1, rng, nn_name, nn_p_name)
ModelingToolkit.getname(NN) # :nn_name # Should be :custom_nn_name
ModelingToolkit.getname(NN_p) # :custom_nn_p_name
`

Relevant interfaces:
Function: getname(x)
Location: ModelingToolkit.getname (defined in Symbolics.jl)
Inputs: 
- **x**: a symbolic entity (variable, symbolic function, or an element of an array returned by a symbolic function, e.g., `vs[1]` where `vs = @variables f1(..)[1:3]`).
Outputs: 
- **Symbol**: the base name of the symbolic entity (e.g., `:f1`).
Description: Retrieves the underlying name of a Symbolics object, correctly handling cases where the object originates from an interpolated symbolic function returning an array and is subsequently indexed. This ensures `getname(vs[i])` yields the original function name rather than an indexed or mangled identifier.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

