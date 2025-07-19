#!/bin/bash
set -e  # 遇到错误立即退出

echo "=== GPUDrive Rebuild Script ==="

# 确保在正确的目录
if [ ! -f "Dockerfile" ]; then
    echo "Error: Please run this script from the gpudrive root directory"
    exit 1
fi

echo "1. Cleaning build directories and cache..."
rm -rf build ./gpudrive_cache

echo "2. Creating build directory..."
mkdir -p build
cd build

echo "3. Configuring CMake..."
uv run cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5

echo "4. Cleaning external tar files..."
find external -type f -name "*.tar" -delete

echo "5. Creating CUDA stub symlink (for compilation)..."
ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1

echo "6. Building with uv..."
LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs/:$LD_LIBRARY_PATH uv run make -j$(nproc)

echo "7. Cleaning up CUDA stub symlink..."
rm -f /usr/local/cuda/lib64/stubs/libcuda.so.1

echo "8. Returning to root directory..."
cd ..

echo "9. Setting up Python environment..."
# 确保Python路径正确设置
export PYTHONPATH=/workspace/gpudrive/build:/workspace/gpudrive/.venv/lib/python3.11/site-packages:$PYTHONPATH
export VIRTUAL_ENV=/workspace/gpudrive/.venv
export PATH=/workspace/gpudrive/.venv/bin:$PATH

echo "10. Verifying build..."
# 检查关键文件是否存在
if [ -f "build/madrona_gpudrive.cpython-311-x86_64-linux-gnu.so" ]; then
    echo "✓ C++ library built successfully"
else
    echo "✗ C++ library not found!"
    exit 1
fi

echo "11. Testing Python import..."
python -c "import madrona_gpudrive; print('✓ Python import successful')" || {
    echo "✗ Python import failed!"
    exit 1
}

echo ""
echo "=== Build completed successfully! ==="
echo "C++ library: build/madrona_gpudrive.cpython-311-x86_64-linux-gnu.so"
echo "Python package: Available via import madrona_gpudrive"
echo ""
echo "Note: The MADRONA_MWGPU_KERNEL_CACHE is set to ./gpudrive_cache"
echo "      This will speed up subsequent builds by caching CUDA kernels."