#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to generate protobuf files.
Run this script to generate funboost_grpc_pb2.py and funboost_grpc_pb2_grpc.py files.
"""

import subprocess
import sys
import os


def generate_protobuf():
    """
    Generate protobuf files
    """
    try:
        # Execute protoc command
        cmd = [
            sys.executable, '-m', 'grpc_tools.protoc',
            '--proto_path=.',
            '--python_out=.',
            '--grpc_python_out=.',
            'funboost_grpc.proto'
        ]
        
        print("Generating protobuf files...")
        print(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("protobuf files generated successfully!")
            print("Generated files:")
            if os.path.exists('funboost_grpc_pb2.py'):
                print("  - funboost_grpc_pb2.py")
            if os.path.exists('funboost_grpc_pb2_grpc.py'):
                print("  - funboost_grpc_pb2_grpc.py")
        else:
            print("protobuf file generation failed!")
            print(f"Error message: {result.stderr}")
            
    except Exception as e:
        print(f"Exception occurred during generation: {e}")


if __name__ == '__main__':
    generate_protobuf()
