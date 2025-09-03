#!/usr/bin/env python3
"""
Integration test runner script.
Runs all integration tests and generates a comprehensive report.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class IntegrationTestRunner:
    """Integration test runner with reporting."""

    def __init__(self, verbose: bool = False, fast: bool = False):
        self.verbose = verbose
        self.fast = fast
        self.project_root = Path(__file__).parent.parent.parent
        self.backend_root = self.project_root / "backend"

    def run_command(self, command: list[str], cwd: Path = None) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        if cwd is None:
            cwd = self.backend_root

        if self.verbose:
            print(f"Running: {' '.join(command)} in {cwd}")

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def run_pytest_tests(self, test_files: list[str], markers: list[str] = None) -> dict:
        """Run pytest tests and return results."""
        command = ["python", "-m", "pytest", "-v"]

        if markers:
            for marker in markers:
                command.extend(["-m", marker])

        if self.fast:
            command.extend(["-x", "--tb=short"])  # Stop on first failure, short traceback
        else:
            command.extend(["--tb=long"])  # Long traceback for debugging

        command.extend(test_files)

        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(command)
        end_time = time.time()

        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration": end_time - start_time,
            "success": exit_code == 0,
        }

    def run_docker_integration_tests(self) -> dict:
        """Run Docker integration tests."""
        print("🐳 Running Docker integration tests...")

        test_files = ["tests/test_docker_integration.py"]
        markers = ["integration"] if not self.fast else None

        return self.run_pytest_tests(test_files, markers)

    def run_configuration_tests(self) -> dict:
        """Run configuration integration tests."""
        print("⚙️  Running configuration integration tests...")

        test_files = ["tests/test_integration_config.py"]

        return self.run_pytest_tests(test_files)

    def run_middleware_integration_tests(self) -> dict:
        """Run middleware integration tests."""
        print("🔗 Running middleware integration tests...")

        test_files = ["tests/test_middleware_integration.py"]

        return self.run_pytest_tests(test_files)

    def run_end_to_end_tests(self) -> dict:
        """Run end-to-end flow tests."""
        print("🔄 Running end-to-end flow tests...")

        test_files = ["tests/test_end_to_end_flows.py"]

        return self.run_pytest_tests(test_files)

    def run_logging_error_tests(self) -> dict:
        """Run logging and error handling tests."""
        print("📝 Running logging and error handling tests...")

        test_files = ["tests/test_logging_error_verification.py"]

        return self.run_pytest_tests(test_files)

    def run_comprehensive_tests(self) -> dict:
        """Run comprehensive integration tests."""
        print("🎯 Running comprehensive integration tests...")

        test_files = ["tests/test_comprehensive_integration.py"]
        markers = ["integration"] if not self.fast else None

        return self.run_pytest_tests(test_files, markers)

    def run_all_tests(self) -> dict[str, dict]:
        """Run all integration tests."""
        print("🚀 Starting integration test suite...")
        print(f"Project root: {self.project_root}")
        print(f"Backend root: {self.backend_root}")
        print(f"Fast mode: {self.fast}")
        print(f"Verbose: {self.verbose}")
        print("-" * 60)

        test_suites = {
            "configuration": self.run_configuration_tests,
            "middleware": self.run_middleware_integration_tests,
            "end_to_end": self.run_end_to_end_tests,
            "logging_error": self.run_logging_error_tests,
            "comprehensive": self.run_comprehensive_tests,
        }

        # Add Docker tests only if not in fast mode
        if not self.fast:
            test_suites["docker"] = self.run_docker_integration_tests

        results = {}
        total_start_time = time.time()

        for suite_name, test_func in test_suites.items():
            try:
                results[suite_name] = test_func()
            except Exception as e:
                results[suite_name] = {"exit_code": 1, "stdout": "", "stderr": str(e), "duration": 0, "success": False}

            # Print immediate results
            result = results[suite_name]
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            duration = result["duration"]
            print(f"{status} {suite_name} ({duration:.2f}s)")

            if not result["success"] and self.verbose:
                print(f"STDERR: {result['stderr']}")
                print(f"STDOUT: {result['stdout']}")

            print("-" * 60)

        total_duration = time.time() - total_start_time
        # Calculate summary excluding the _summary key itself
        test_results = {k: v for k, v in results.items() if k != "_summary"}
        results["_summary"] = {
            "total_duration": total_duration,
            "total_suites": len(test_suites),
            "passed_suites": sum(1 for r in test_results.values() if r.get("success", False)),
            "failed_suites": sum(1 for r in test_results.values() if not r.get("success", False)),
        }

        return results

    def print_summary_report(self, results: dict[str, dict]):
        """Print summary report."""
        summary = results.get("_summary", {})

        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY REPORT")
        print("=" * 60)

        print(f"Total Duration: {summary.get('total_duration', 0):.2f}s")
        print(f"Total Suites: {summary.get('total_suites', 0)}")
        print(f"Passed: {summary.get('passed_suites', 0)}")
        print(f"Failed: {summary.get('failed_suites', 0)}")

        print("\nDetailed Results:")
        print("-" * 40)

        for suite_name, result in results.items():
            if suite_name == "_summary":
                continue

            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            duration = result.get("duration", 0)
            print(f"{status} {suite_name:<20} ({duration:.2f}s)")

        # Overall status
        overall_success = summary.get("failed_suites", 1) == 0
        overall_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"

        print("\n" + "=" * 60)
        print(f"🎯 OVERALL STATUS: {overall_status}")
        print("=" * 60)

        return overall_success

    def generate_detailed_report(self, results: dict[str, dict], output_file: Path = None):
        """Generate detailed test report."""
        if output_file is None:
            output_file = self.backend_root / "test_results" / "integration_test_report.txt"

        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, "w") as f:
            f.write("INTEGRATION TEST DETAILED REPORT\n")
            f.write("=" * 60 + "\n\n")

            summary = results.get("_summary", {})
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {summary.get('total_duration', 0):.2f}s\n")
            f.write(f"Total Suites: {summary.get('total_suites', 0)}\n")
            f.write(f"Passed: {summary.get('passed_suites', 0)}\n")
            f.write(f"Failed: {summary.get('failed_suites', 0)}\n\n")

            for suite_name, result in results.items():
                if suite_name == "_summary":
                    continue

                f.write(f"\n{suite_name.upper()} TEST SUITE\n")
                f.write("-" * 40 + "\n")
                f.write(f"Status: {'PASSED' if result.get('success', False) else 'FAILED'}\n")
                f.write(f"Duration: {result.get('duration', 0):.2f}s\n")
                f.write(f"Exit Code: {result.get('exit_code', 'N/A')}\n\n")

                if result.get("stdout"):
                    f.write("STDOUT:\n")
                    f.write(result["stdout"])
                    f.write("\n\n")

                if result.get("stderr"):
                    f.write("STDERR:\n")
                    f.write(result["stderr"])
                    f.write("\n\n")

        print(f"📄 Detailed report saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-f", "--fast", action="store_true", help="Fast mode (skip slow tests)")
    parser.add_argument("-r", "--report", help="Generate detailed report to file")
    parser.add_argument(
        "--suite",
        choices=["docker", "configuration", "middleware", "end_to_end", "logging_error", "comprehensive", "all"],
        default="all",
        help="Run specific test suite",
    )

    args = parser.parse_args()

    runner = IntegrationTestRunner(verbose=args.verbose, fast=args.fast)

    if args.suite == "all":
        results = runner.run_all_tests()
    else:
        # Run specific suite
        suite_methods = {
            "docker": runner.run_docker_integration_tests,
            "configuration": runner.run_configuration_tests,
            "middleware": runner.run_middleware_integration_tests,
            "end_to_end": runner.run_end_to_end_tests,
            "logging_error": runner.run_logging_error_tests,
            "comprehensive": runner.run_comprehensive_tests,
        }

        if args.suite in suite_methods:
            print(f"Running {args.suite} test suite...")
            result = suite_methods[args.suite]()
            results = {args.suite: result}
        else:
            print(f"Unknown test suite: {args.suite}")
            sys.exit(1)

    # Print summary
    overall_success = runner.print_summary_report(results)

    # Generate detailed report if requested
    if args.report:
        report_file = Path(args.report)
        runner.generate_detailed_report(results, report_file)

    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
