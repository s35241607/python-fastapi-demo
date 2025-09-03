#!/usr/bin/env python3
"""
Configuration management CLI utility
"""

import argparse
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.core.config_validator import validate_configuration
from app.core.environment import Environment, get_environment_info, set_environment


def validate_config(environment: str = None):
    """Validate configuration for specified environment"""
    if environment:
        set_environment(Environment(environment))

    try:
        settings = get_settings()
        report = validate_configuration(settings)

        print("Configuration Validation Report")
        print(f"{'=' * 40}")
        print(f"Environment: {report['environment']}")
        print(f"Valid: {'✅ Yes' if report['valid'] else '❌ No'}")
        print()

        if report["errors"]:
            print("Errors:")
            for error in report["errors"]:
                print(f"  ❌ {error}")
            print()

        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"  ⚠️  {warning}")
            print()

        print("Configuration Summary:")
        summary = report["config_summary"]
        for key, value in summary.items():
            print(f"  {key}: {value}")

        return report["valid"]

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def show_environment_info():
    """Show current environment information"""
    info = get_environment_info()

    print("Environment Information")
    print("=" * 30)
    print(f"Current Environment: {info['current_environment']}")
    print(f"Environment Variable: {info['environment_variable']}")
    print(f"Config File: {info['env_file']}")
    print(f"Config File Exists: {'✅ Yes' if info['env_file_exists'] else '❌ No'}")
    print(f"Available Environments: {', '.join(info['available_environments'])}")


def list_config_files():
    """List all available configuration files"""
    print("Available Configuration Files")
    print("=" * 35)

    for env in Environment:
        env_file = f".env.{env.value}"
        exists = os.path.exists(env_file)
        status = "✅ exists" if exists else "❌ missing"
        print(f"  {env_file:<20} {status}")

    # Check for default .env file
    default_env = ".env"
    exists = os.path.exists(default_env)
    status = "✅ exists" if exists else "❌ missing"
    print(f"  {default_env:<20} {status}")


def validate_all_environments():
    """Validate configuration for all environments"""
    print("Validating All Environments")
    print("=" * 35)

    results = {}
    for env in Environment:
        print(f"\n🔍 Validating {env.value}...")
        try:
            set_environment(env)
            settings = get_settings()
            report = validate_configuration(settings)
            results[env.value] = report["valid"]

            if report["valid"]:
                print(f"  ✅ {env.value}: Valid")
            else:
                print(f"  ❌ {env.value}: Invalid")
                for error in report["errors"]:
                    print(f"    - {error}")

        except Exception as e:
            print(f"  ❌ {env.value}: Error - {e}")
            results[env.value] = False

    print("\n📊 Summary:")
    for env, valid in results.items():
        status = "✅ Valid" if valid else "❌ Invalid"
        print(f"  {env:<12} {status}")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(description="Configuration management utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--env", choices=[e.value for e in Environment], help="Environment to validate (default: current)"
    )

    # Environment info command
    subparsers.add_parser("info", help="Show environment information")

    # List config files command
    subparsers.add_parser("list", help="List configuration files")

    # Validate all environments command
    subparsers.add_parser("validate-all", help="Validate all environments")

    args = parser.parse_args()

    if args.command == "validate":
        success = validate_config(args.env)
        sys.exit(0 if success else 1)
    elif args.command == "info":
        show_environment_info()
    elif args.command == "list":
        list_config_files()
    elif args.command == "validate-all":
        success = validate_all_environments()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
