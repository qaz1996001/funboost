#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import generated protobuf files
import hello_pb2
import hello_pb2_grpc


def test_original():
    """
    Original version - single-threaded synchronous calls
    """
    print("\n=== Test 1: Original version (single-threaded sync) ===")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)

        time_start = time.time()
        for i in range(1000):  # Reduced to 1000 calls for testing
            request = hello_pb2.HelloRequest(name=f"World_{i}")
            try:
                response = stub.SayHello(request)
                # No print, just receive
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000 calls took: {total_time:.3f} seconds")
        print(f"Average per call: {total_time/1000*1000:.3f} ms")
        print(f"QPS: {1000/total_time:.0f}")


def test_channel_options():
    """
    Optimized version 1 - using connection pool and optimized channel options
    """
    print("\n=== Test 2: Optimized channel options ===")

    # Optimized channel options
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ('grpc.max_connection_idle_ms', 30000),
    ]

    with grpc.insecure_channel('localhost:50051', options=options) as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)

        time_start = time.time()
        for i in range(1000):
            request = hello_pb2.HelloRequest(name=f"World_{i}")
            try:
                response = stub.SayHello(request)
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000 calls took: {total_time:.3f} seconds")
        print(f"Average per call: {total_time/1000*1000:.3f} ms")
        print(f"QPS: {1000/total_time:.0f}")


def test_thread_pool():
    """
    Optimized version 2 - using thread pool for concurrent calls
    """
    print("\n=== Test 3: Thread pool concurrent calls ===")

    def make_call(stub, i):
        request = hello_pb2.HelloRequest(name=f"World_{i}")
        try:
            response = stub.SayHello(request)
            return True
        except grpc.RpcError as e:
            print(f"gRPC call failed: {e}")
            return False

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)

        time_start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_call, stub, i) for i in range(1000)]

            success_count = 0
            for future in as_completed(futures):
                if future.result():
                    success_count += 1

        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000 calls took: {total_time:.3f} seconds")
        print(f"Successful calls: {success_count}/1000")
        print(f"Average per call: {total_time/1000*1000:.3f} ms")
        print(f"QPS: {1000/total_time:.0f}")


def test_multiple_connections():
    """
    Optimized version 3 - using multiple connections
    """
    print("\n=== Test 4: Multiple connections concurrent ===")

    def worker(worker_id, calls_per_worker):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = hello_pb2_grpc.HelloServiceStub(channel)

            for i in range(calls_per_worker):
                request = hello_pb2.HelloRequest(name=f"Worker_{worker_id}_Call_{i}")
                try:
                    response = stub.SayHello(request)
                except grpc.RpcError as e:
                    print(f"Worker {worker_id} call failed: {e}")

    num_workers = 5
    calls_per_worker = 200  # 5*200 = 1000

    time_start = time.time()
    threads = []
    for worker_id in range(num_workers):
        thread = threading.Thread(target=worker, args=(worker_id, calls_per_worker))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    time_end = time.time()
    total_time = time_end - time_start
    print(f"1000 calls took: {total_time:.3f} seconds")
    print(f"Average per call: {total_time/1000*1000:.3f} ms")
    print(f"QPS: {1000/total_time:.0f}")


def test_batch_calls():
    """
    Optimized version 4 - pre-create request objects to reduce object creation overhead
    """
    print("\n=== Test 5: Pre-created request objects ===")

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)

        # Pre-create all request objects
        requests = [hello_pb2.HelloRequest(name=f"World_{i}") for i in range(1000)]

        time_start = time.time()
        for request in requests:
            try:
                response = stub.SayHello(request)
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        time_end = time.time()
        total_time = time_end - time_start
        print(f"1000 calls took: {total_time:.3f} seconds")
        print(f"Average per call: {total_time/1000*1000:.3f} ms")
        print(f"QPS: {1000/total_time:.0f}")


if __name__ == '__main__':
    print("gRPC Performance Test Comparison")
    print("=" * 50)

    # Run various tests
    test_original()
    test_channel_options()
    test_batch_calls()
    test_thread_pool()
    test_multiple_connections()

    print("\n" + "=" * 50)
    print("Tests complete!")
    print("\nAnalysis:")
    print("1. Reasons why the original version is slow:")
    print("   - Single-threaded synchronous calls, no concurrency")
    print("   - Creates new request objects each time")
    print("   - No optimization of gRPC connection parameters")
    print("\n2. Optimization recommendations:")
    print("   - Use thread pool or multiple connections for concurrency")
    print("   - Pre-create request objects")
    print("   - Adjust gRPC connection parameters")
    print("   - Consider using async gRPC (grpcio-async)")
