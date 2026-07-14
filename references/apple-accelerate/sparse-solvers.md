---
topic_id: "v2:NIOF"
topic_path: "apple-accelerate/sparse-solvers"
semantic_id: "-32KV6078ViqxPMfh7ab2QR3VtZc4AAI"
related_ids:
  - "8_1kxm84mVCyhuKeB4aZ9wx5jd9V4AAG"
  - "9-_ohzE9PdqiUeOKQqwBOA5m3ldc4AAM"
---
# Sparse Solvers & Sparse BLAS

Source:

- https://developer.apple.com/documentation/accelerate/sparse_solvers
- https://developer.apple.com/documentation/accelerate/sparse-blas
- https://developer.apple.com/documentation/accelerate/creating_sparse_matrices

For matrices that are mostly zeros — finite-element stiffness matrices, graph Laplacians,
recommendation systems — dense LAPACK wastes memory and time storing and multiplying zeros.
Accelerate's Sparse Solvers store only nonzeros and solve `Ax = b` accordingly.

## Two layers

- **Sparse BLAS** — sparse analogs of BLAS: sparse matrix × dense vector/matrix
  (`sparse_matrix_vector_product_dense_float`), triangular solves, insertion. Types:
  `sparse_matrix_float` / `sparse_matrix_double`, built with `sparse_matrix_create_float`,
  populated via `sparse_insert_entry` / `sparse_insert_col` / `sparse_insert_row`, then
  `sparse_commit` to finalize before use.
- **Sparse Solvers** — factorization-based direct solvers plus iterative solvers:
  - **Direct:** `SparseFactor` → `SparseSolve`. Factorization types include
    `SparseFactorizationCholesky` (symmetric positive-definite), `SparseFactorizationLDLT`
    (symmetric indefinite), `SparseFactorizationQR` (least squares), and LU.
  - **Iterative:** conjugate gradient, GMRES, LSMR via `SparseSolve` with a method + a
    preconditioner (`SparsePreconditionerDiagonal`, ILU-style, etc.).

## Sparse formats

- **Coordinate / entry lists** at construction (you insert `(row, col, value)` triples).
- **CSC (compressed sparse column)** is the internal/committed form. `SparseMatrix_Double`
  exposes `columnStarts`, `rowIndices`, `data` — column-major, like the rest of LAPACK.
- Symmetric matrices store only one triangle; you declare which via the attributes
  (`SparseAttributes_t.triangle` + `.kind = SparseSymmetric`).

## Typical direct-solve flow

1. Build `SparseMatrixStructure` (CSC index arrays) + values → `SparseMatrix_Double`.
2. `factorization = SparseFactor(SparseFactorizationCholesky, matrix)`.
3. `SparseSolve(factorization, b, &x)` — reuse the factorization for many right-hand sides.
4. `SparseCleanup(factorization)` and `SparseCleanup(matrix)` when done.

## Gotchas

- **Commit before you use it.** A Sparse BLAS matrix built with `sparse_insert_*` is not
  usable until `sparse_commit`. Multiplying an uncommitted matrix returns wrong/empty results.
- **Symmetric means store one triangle _and say so_.** If you set `.kind = SparseSymmetric`
  but insert both triangles, entries are double-counted; if you store one triangle but leave
  it unsymmetric, the solver reads only half the matrix. The attribute and the data must agree.
- **CSC, column-major.** Same Fortran orientation as LAPACK. Feeding CSR index arrays into a
  CSC-expecting call silently transposes your system.
- **Reuse the factorization.** `SparseFactor` is the expensive step; if you solve for many
  `b`'s with the same `A`, factor once and call `SparseSolve` repeatedly. Re-factoring per
  solve throws away the whole point.
- **Cleanup is manual.** `SparseFactor`/`SparseMatrix_*` allocate; `SparseCleanup` frees.
  Forgetting it leaks (these can be large).
- **Sparsity has a break-even.** Below ~a few-percent fill, sparse wins big; a "sparse"
  matrix that's actually 40% dense is faster in dense LAPACK. Know your fill ratio.

### See also

- [[blas-and-lapack]] — dense linear algebra; the right choice above the sparsity break-even.
