# Builds firmware in Dev Container environment
cd /workspaces/zmk/app
west build -d build/sofle_left -b nice_nano_v2 -- -DZMK_CONFIG="/workspaces/zmk-config/config" -DZMK_EXTRA_MODULES="/workspaces/zmk-config/zmk-userspace" -DSHIELD="sofle_left"  
west build -d build/sofle_right -b nice_nano_v2 -- -DZMK_CONFIG="/workspaces/zmk-config/config" -DZMK_EXTRA_MODULES="/workspaces/zmk-config/zmk-userspace" -DSHIELD="sofle_right"
mkdir -p /workspaces/zmk-config/out/
cp build/sofle_left/zephyr/zmk.uf2 /workspaces/zmk-config/out/sofle_left.uf2
cp build/sofle_right/zephyr/zmk.uf2 /workspaces/zmk-config/out/sofle_right.uf2
