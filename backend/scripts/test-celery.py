#!/usr/bin/env python3
"""
Test script to verify Celery and Redis integration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.workers.celery_app import celery_app
from app.workers.tasks import run_build, run_simulation


def test_celery_connection():
    """Test if Celery can connect to Redis"""
    print("Testing Celery connection to Redis...")

    try:
        # Check if broker is accessible
        celery_app.connection().ensure_connection(max_retries=3)
        print("✓ Successfully connected to Redis broker")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        return False


def test_worker_ping():
    """Test if workers are running and responsive"""
    print("\nTesting worker availability...")

    try:
        # Send ping to workers
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            print(f"✓ Found {len(stats)} active worker(s):")
            for worker_name, worker_stats in stats.items():
                print(f"  - {worker_name}")
                print(f"    Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
                print(f"    Max concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
            return True
        else:
            print("✗ No active workers found")
            print("  Start a worker with: ./scripts/start-worker.sh")
            return False
    except Exception as e:
        print(f"✗ Failed to inspect workers: {e}")
        return False


def test_queues():
    """Test if queues are configured correctly"""
    print("\nTesting queue configuration...")

    try:
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues()

        if active_queues:
            print("✓ Active queues:")
            for worker_name, queues in active_queues.items():
                print(f"  Worker: {worker_name}")
                for queue in queues:
                    print(f"    - {queue['name']} (routing_key: {queue.get('routing_key', 'N/A')})")
            return True
        else:
            print("✗ No active queues found")
            return False
    except Exception as e:
        print(f"✗ Failed to inspect queues: {e}")
        return False


def test_registered_tasks():
    """List registered tasks"""
    print("\nRegistered tasks:")

    registered = celery_app.control.inspect().registered()
    if registered:
        for worker_name, tasks in registered.items():
            print(f"  Worker: {worker_name}")
            for task in tasks:
                if 'app.workers.tasks' in task:
                    print(f"    - {task}")
        return True
    else:
        print("  No tasks registered")
        return False


def main():
    print("=" * 60)
    print("Celery + Redis Integration Test")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Connection", test_celery_connection()))
    results.append(("Workers", test_worker_ping()))
    results.append(("Queues", test_queues()))
    results.append(("Tasks", test_registered_tasks()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    print()
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Celery is properly configured.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
