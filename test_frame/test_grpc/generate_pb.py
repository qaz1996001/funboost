#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to generate protobuf files
Run this script to generate hello_pb2.py and hello_pb2_grpc.py files
"""

import subprocess
import sys
import os


def generate_protobuf():
    """
    Generate protobuf files
    """
    try:
        # Execute the protoc command
        cmd = [
            sys.executable, '-m', 'grpc_tools.protoc',
            '--proto_path=.',
            '--python_out=.',
            '--grpc_python_out=.',
            'hello.proto'
        ]

        print("Generating protobuf files...")
        print(f"Executing command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("protobuf files generated successfully!")
            print("Generated files:")
            if os.path.exists('hello_pb2.py'):
                print("  - hello_pb2.py")
            if os.path.exists('hello_pb2_grpc.py'):
                print("  - hello_pb2_grpc.py")
        else:
            print("Failed to generate protobuf files!")
            print(f"Error: {result.stderr}")

    except Exception as e:
        print(f"Exception during generation: {e}")


if __name__ == '__main__':
    generate_protobuf()
