#!/usr/bin/env python3
"""Exact-arithmetic certificate for two counterexamples extracted from the
Alpöge Jacobian-conjecture counterexample (announced 19 July 2026):

  (1) the injective, non-surjective endomorphism of the third Weyl algebra
      A_3 (Dixmier conjecture false for n >= 3; first published by
      Omniscience Research Agent and J. Pickhardt, 19 July 2026 — this
      script is a runnable certificate for the identities their paper and
      our companion note rely on);

  (2) the injective, non-surjective Poisson endomorphism of the standard
      symplectic Poisson algebra k[x1..x3, xi1..xi3] (Poisson conjecture,
      explicit instance — companion note, Theorem "Poisson").

With F the Alpöge map, J = JF its Jacobian and G = (J^T)^{-1} (polynomial
entries since det J = -2), the two structures are

  Weyl:    phi(x_i) = F_i,  phi(d_j)  = D_j   = sum_k G[j,k] d_k
  Poisson: psi(x_i) = F_i,  psi(xi_j) = eta_j = sum_k G[j,k] xi_k

Well-definedness of BOTH reduces to identities certified here, exactly,
over Q (every check is a sympy Poly over domain QQ tested for literal
vanishing — no floats anywhere):

  det J == -2                      (Keller condition)
  three-point collision            (F not injective)
  (R1)  G * J^T == I               ([D_j, F_i] = delta_ij; {F_i, eta_j} = delta_ij)
  (R2)  all [D_i, D_j] == 0        (flatness of the inverse-Jacobian frame)
  (P1)  {F_i, F_j} == 0            (Poisson, checked directly)
  (P2)  {F_i, eta_j} == delta_ij   (Poisson, checked directly)
  (P3)  {eta_i, eta_j} == 0        (Poisson, checked directly)
  det G == -1/2                    (invertibility of the symbol substitution)

The bracket used is the standard symplectic one:
  {f, g} = sum_k (df/dx_k dg/dxi_k - df/dxi_k dg/dx_k),  {x_i, xi_j} = delta_ij.

The script also writes G.json (the nine entries of G as exact polynomial
strings) so the endomorphism is explicit without re-derivation.

Exit code 0 iff every identity holds exactly.
"""

import json
import platform
import sys

import sympy as sp


def build_keller_map() -> tuple[list[sp.Expr], list[sp.Symbol]]:
    """Return the Alpöge Keller map and its variables."""
    x, y, z = sp.symbols('x y z')
    f1 = (1 + x*y)**3 * z + y**2 * (1 + x*y) * (4 + 3*x*y)
    f2 = y + 3*x*(1 + x*y)**2 * z + 3*x*y**2 * (4 + 3*x*y)
    f3 = 2*x - 3*x**2*y - x**3*z
    return [f1, f2, f3], [x, y, z]


def is_zero_poly(expr: sp.Expr, gens: list[sp.Symbol]) -> bool:
    """Certify expr == 0 as a polynomial over QQ (exact, no floats)."""
    return sp.Poly(sp.expand(expr), *gens, domain='QQ').is_zero


def main() -> int:
    print(f'python {platform.python_version()}  sympy {sp.__version__}')
    print()

    F, X = build_keller_map()
    n = len(X)
    xi = list(sp.symbols('xi1 xi2 xi3'))
    allv = X + xi

    def bracket(f: sp.Expr, g: sp.Expr) -> sp.Expr:
        return sum(sp.diff(f, X[k]) * sp.diff(g, xi[k])
                   - sp.diff(f, xi[k]) * sp.diff(g, X[k]) for k in range(n))

    checks: list[tuple[str, bool]] = []

    J = sp.Matrix(F).jacobian(X)
    det = sp.expand(J.det())
    checks.append(('det J == -2 identically', det == -2))

    pts = [(sp.Integer(0), sp.Integer(0), sp.Rational(-1, 4)),
           (sp.Integer(1), sp.Rational(-3, 2), sp.Rational(13, 2)),
           (sp.Integer(-1), sp.Rational(3, 2), sp.Rational(13, 2))]
    target = (sp.Rational(-1, 4), sp.Integer(0), sp.Integer(0))
    checks.append(('collision points pairwise distinct', len(set(pts)) == len(pts)))
    for p in pts:
        img = tuple(sp.expand(f.subs(dict(zip(X, p)))) for f in F)
        checks.append((f'F({p}) == {target}', img == target))

    # G = (J^T)^{-1} = adj(J^T)/det: polynomial entries since det = -2.
    G = (J.T).adjugate() / det
    G = G.applyfunc(sp.expand)

    checks.append(('det G == -1/2', sp.expand(G.det()) == sp.Rational(-1, 2)))

    R1 = G * J.T - sp.eye(n)
    ok_r1 = all(is_zero_poly(R1[i, j], X) for i in range(n) for j in range(n))
    checks.append(('(R1) G * J^T == I', ok_r1))

    ok_r2 = True
    for i in range(n):
        for j in range(i + 1, n):
            for l in range(n):
                expr = sum(G[i, k] * sp.diff(G[j, l], X[k])
                           - G[j, k] * sp.diff(G[i, l], X[k]) for k in range(n))
                ok_r2 &= is_zero_poly(expr, X)
    checks.append(('(R2) all [D_i, D_j] == 0 (flatness)', ok_r2))

    eta = [sum(G[j, k] * xi[k] for k in range(n)) for j in range(n)]

    ok_p1 = all(is_zero_poly(bracket(F[i], F[j]), allv)
                for i in range(n) for j in range(n))
    checks.append(('(P1) {F_i, F_j} == 0', ok_p1))

    ok_p2 = all(is_zero_poly(bracket(F[i], eta[j]) - (1 if i == j else 0), allv)
                for i in range(n) for j in range(n))
    checks.append(('(P2) {F_i, eta_j} == delta_ij', ok_p2))

    ok_p3 = all(is_zero_poly(bracket(eta[i], eta[j]), allv)
                for i in range(n) for j in range(n))
    checks.append(('(P3) {eta_i, eta_j} == 0', ok_p3))

    with open('G.json', 'w') as fh:
        json.dump({'convention': 'G = (J^T)^{-1}, J_ik = dF_i/dx_k, order x,y,z',
                   'entries': [[str(G[i, j]) for j in range(n)] for i in range(n)]},
                  fh, indent=1)

    width = max(len(name) for name, _ in checks)
    all_ok = True
    for name, ok in checks:
        all_ok &= ok
        print(f'{name:<{width}}  {"PASS" if ok else "FAIL"}')

    print()
    if all_ok:
        print('ALL CHECKS PASS (exact, over QQ). G written to G.json.')
        print('Certified: phi is a well-defined endomorphism of A_3 and psi a')
        print('well-defined Poisson endomorphism; F is a non-injective Keller')
        print('map. The non-surjectivity arguments are in the companion note.')
    else:
        print('CHECK FAILURE — witness NOT certified.')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
