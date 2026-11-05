"""Model specifications and repeatable fitting for segmentation candidates."""

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import Birch, KMeans
from sklearn.mixture import GaussianMixture


@dataclass(frozen=True)
class ModelSpec:
    method: str
    config_id: str
    requested_clusters: int
    parameters: dict[str, Any]


@dataclass(frozen=True)
class CandidateResult:
    spec: ModelSpec
    labels: np.ndarray
    fit_seconds: tuple[float, ...]
    metrics: dict[str, Any]
    membership_probability: np.ndarray | None = None

    @property
    def median_fit_seconds(self) -> float:
        return float(np.median(self.fit_seconds))


def build_candidate_specs(
    k_values: Iterable[int] = range(3, 7),
    birch_thresholds: Iterable[float] = (0.3, 0.5, 0.7),
    seed: int = 42,
) -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for clusters in k_values:
        if clusters < 2:
            raise ValueError("Every candidate must request at least two clusters.")
        specs.append(
            ModelSpec(
                method="kmeans",
                config_id=f"kmeans_k{clusters}",
                requested_clusters=clusters,
                parameters={
                    "n_clusters": clusters,
                    "random_state": seed,
                    "n_init": 20,
                    "max_iter": 300,
                    "algorithm": "lloyd",
                },
            )
        )
        specs.append(
            ModelSpec(
                method="gmm",
                config_id=f"gmm_k{clusters}",
                requested_clusters=clusters,
                parameters={
                    "n_components": clusters,
                    "random_state": seed,
                    "covariance_type": "full",
                    "n_init": 3,
                    "max_iter": 200,
                    "reg_covar": 1e-6,
                },
            )
        )
        for threshold in birch_thresholds:
            specs.append(
                ModelSpec(
                    method="birch",
                    config_id=f"birch_k{clusters}_t{threshold:g}",
                    requested_clusters=clusters,
                    parameters={
                        "n_clusters": clusters,
                        "threshold": float(threshold),
                        "branching_factor": 50,
                    },
                )
            )
    return specs


def build_model(spec: ModelSpec):
    if spec.method == "kmeans":
        return KMeans(**spec.parameters)
    if spec.method == "gmm":
        return GaussianMixture(**spec.parameters)
    if spec.method == "birch":
        return Birch(**spec.parameters)
    raise ValueError(f"Unsupported segmentation method: {spec.method}")


def _fit_once(features: np.ndarray, spec: ModelSpec):
    model = build_model(spec)
    started = perf_counter()
    labels = np.asarray(model.fit_predict(features), dtype="int32")
    elapsed = perf_counter() - started
    return model, labels, elapsed


def fit_candidate(
    features: np.ndarray,
    spec: ModelSpec,
    repeats: int = 3,
    warmup: bool = True,
) -> CandidateResult:
    """Fit one deterministic candidate and return labels from the final measured run."""
    matrix = np.asarray(features, dtype="float64")
    if matrix.ndim != 2 or len(matrix) < 2 or not np.isfinite(matrix).all():
        raise ValueError("Model features must be a finite two-dimensional matrix.")
    if repeats < 1:
        raise ValueError("Benchmark repeats must be at least one.")
    if warmup:
        _fit_once(matrix, spec)

    durations: list[float] = []
    final_model = None
    final_labels = None
    for _ in range(repeats):
        final_model, final_labels, elapsed = _fit_once(matrix, spec)
        durations.append(elapsed)
    assert final_model is not None and final_labels is not None

    metrics: dict[str, Any] = {}
    probabilities = None
    if spec.method == "kmeans":
        metrics["inertia"] = float(final_model.inertia_)
        metrics["iterations"] = int(final_model.n_iter_)
    elif spec.method == "gmm":
        metrics["converged"] = bool(final_model.converged_)
        metrics["iterations"] = int(final_model.n_iter_)
        metrics["lower_bound"] = float(final_model.lower_bound_)
        metrics["bic"] = float(final_model.bic(matrix))
        metrics["aic"] = float(final_model.aic(matrix))
        probabilities = final_model.predict_proba(matrix).max(axis=1).astype("float64")
    elif spec.method == "birch":
        metrics["subclusters"] = int(len(final_model.subcluster_centers_))

    return CandidateResult(
        spec=spec,
        labels=final_labels,
        fit_seconds=tuple(float(value) for value in durations),
        metrics=metrics,
        membership_probability=probabilities,
    )
