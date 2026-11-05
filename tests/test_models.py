import numpy as np

from src.segmentation.models import ModelSpec, fit_candidate


def clustered_features() -> np.ndarray:
    random = np.random.default_rng(42)
    return np.vstack(
        [
            random.normal((-3, -3, -3), 0.15, size=(30, 3)),
            random.normal((0, 0, 0), 0.15, size=(30, 3)),
            random.normal((3, 3, 3), 0.15, size=(30, 3)),
        ]
    )


def test_all_model_families_fit_and_are_reproducible() -> None:
    specs = [
        ModelSpec(
            "kmeans",
            "kmeans_k3",
            3,
            {"n_clusters": 3, "random_state": 42, "n_init": 10},
        ),
        ModelSpec(
            "gmm",
            "gmm_k3",
            3,
            {
                "n_components": 3,
                "random_state": 42,
                "n_init": 2,
                "covariance_type": "full",
                "reg_covar": 1e-6,
            },
        ),
        ModelSpec(
            "birch",
            "birch_k3_t0.5",
            3,
            {"n_clusters": 3, "threshold": 0.5, "branching_factor": 50},
        ),
    ]
    for spec in specs:
        first = fit_candidate(clustered_features(), spec, repeats=1, warmup=False)
        second = fit_candidate(clustered_features(), spec, repeats=1, warmup=False)
        assert len(np.unique(first.labels)) == 3
        assert np.array_equal(first.labels, second.labels)
        assert first.median_fit_seconds >= 0
