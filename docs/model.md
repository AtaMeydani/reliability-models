# Model definitions

## System state and service reward

All components start healthy. The system operates under these conditions:

- Series: every component is healthy.
- M-of-N: at least $m$ components are healthy. Parallel operation is the $m=1$ case.
- Wheatstone bridge: at least one complete source-to-target path is healthy. Component names must be exactly `C1` through `C5`. The paths are `(C1,C4)`, `(C2,C5)`, `(C1,C3,C5)`, and `(C2,C3,C4)`.

The state reward $g(s)$ is the sum of healthy component capacities when the system operates, otherwise zero. Its expected value is reported as performability.

## Markov solver

There are $2^n$ health states for $n$ components. Healthy components fail at rate `lam` ($\lambda$); failed components repair at rate `mu` ($\mu$). A common-cause shock fails all healthy members of its group. Rates add when multiple causes lead to the same state.

For rate matrix $Q$ and an initially healthy row distribution $\mathbf{p}_0$:

$$
\mathbf{p}(t)=\mathbf{p}_0 e^{Qt}
$$

Let $\mathcal{U}$ be the set of functioning states. Availability is

$$
A(t)=\sum_{s\in\mathcal{U}}p_s(t).
$$

Expected service reward is

$$
\mathbb{E}[g(X(t))]=\sum_s p_s(t)g(s).
$$

Reliability is the probability of never leaving the functioning states. It uses their submatrix $Q_{\mathcal{U}}$, retaining the original diagonal:

$$
R(t)=\mathbf{p}_{0,\mathcal{U}}e^{Q_{\mathcal{U}}t}\mathbf{1}.
$$

Repairs between functioning states remain enabled; probability that leaves this subset does not return.

## Monte Carlo solver

The simulator advances between component failures, repairs, and Poisson common-cause shocks, recording uptime and service reward.

A shock starts repair clocks for newly failed members. Members that were already failed keep their existing repair clocks. Reliability is estimated from first-system-failure times; availability and service reward are averaged at each requested result time.

Sampling intervals are `[start,end)`. The final state is sampled at the simulation horizon before processing any event at that exact time.

## Bayesian solver

The Bayesian solver handles nonrepairable systems with common-cause failures, and instantaneous availability and service reward for independent repairable components. First-failure reliability with repairs and common-cause shocks with repairs use the Markov solver.

For an independent component that starts healthy:

$$
P_i(\mathrm{up},t)=
\frac{\mu_i}{\lambda_i+\mu_i}
+\frac{\lambda_i}{\lambda_i+\mu_i}
 e^{-(\lambda_i+\mu_i)t}.
$$

A zero total rate gives probability one. Without repairs, a common-cause parent represents no shock occurring before $t$. For shock rate $\lambda_c$:

$$
P(\mathrm{no\ shock\ before}\ t)=e^{-\lambda_c t}.
$$

Shared parents preserve component dependence. Joint component probabilities are used for the service reward.

## Analytical solver

The analytical solver handles two parallel, nonrepairable components with equal failure rate $\lambda$ and no common-cause groups. When one component fails, the survivor's failure rate is multiplied by $k$.

$$
R(t)=
\begin{cases}
e^{-2\lambda t}+\dfrac{2}{2-k}
\left(e^{-k\lambda t}-e^{-2\lambda t}\right), & k\ne 2, \\
(1+2\lambda t)e^{-2\lambda t}, & k=2.
\end{cases}
$$

Availability equals reliability because there are no repairs. For equal component capacity $c$:

$$
\mathbb{E}[g(X(t))]=c\left[R(t)+e^{-2\lambda t}\right].
$$

The implementation uses a numerically stable form near $k=2$.

## Assumptions

Failure and repair times are exponential with constant rates. Repairs run independently and in parallel, restoring components to their initial condition.
