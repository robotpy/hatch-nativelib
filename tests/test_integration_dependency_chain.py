from __future__ import annotations


def test_consumer_links_to_installed_provider_and_imports_work(project_factory) -> None:
    provider_root = project_factory.copy_package_fixture("provider-pkg", "provider")

    provider_build = project_factory.run(
        "-m", "build", "--wheel", "--no-isolation", cwd=provider_root
    )
    assert provider_build.returncode == 0, provider_build.stdout + provider_build.stderr
    provider_wheel = next((provider_root / "dist").glob("*.whl"))
    project_factory.env.install_wheel(provider_wheel)

    consumer_root = project_factory.copy_package_fixture("consumer-pkg", "consumer")

    consumer_build = project_factory.run(
        "-m", "build", "--wheel", "--no-isolation", cwd=consumer_root
    )

    assert consumer_build.returncode == 0, consumer_build.stdout + consumer_build.stderr
    consumer_init = (consumer_root / "src/consumer_pkg/_init_consumer.py").read_text(
        encoding="utf-8"
    )
    assert "import provider_pkg._init_provider" in consumer_init

    consumer_wheel = next((consumer_root / "dist").glob("*.whl"))
    project_factory.env.install_wheel(consumer_wheel)

    result = project_factory.run(
        "-c",
        "import consumer_pkg; print(consumer_pkg.consumer_twice_plus_one(10))",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "21"
