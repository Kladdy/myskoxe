set -euo pipefail

install_path="/myskoxe/myskoxe/frendy/frendy_install"
frendy_file_name="frendy_20241030"

mkdir -pv $install_path
cd $install_path

# Check if the file exists. If not, download it. Else, print a message.
if [ ! -f "${frendy_file_name}.tar.gz" ]; then
    wget -c https://rpg.jaea.go.jp/download/frendy/${frendy_file_name}.tar.gz
else
    echo "File '$(pwd)/${frendy_file_name}.tar.gz' already exists, skipping download..."
fi

# Check if the file has been extracted. If not, extract it. Else, print a message.
if [ ! -d "${frendy_file_name}" ]; then
    tar -xvf ${frendy_file_name}.tar.gz
else
    echo "File '$(pwd)/${frendy_file_name}' already exists, skipping extraction..."
fi

cd ${frendy_file_name}/frendy

# Check if file 'frendy/main/frendy.exe' exists. If not, compile it. Else, print a message.
if [ ! -f "main/frendy.exe" ]; then
    ./compile_all.csh
else
    echo "File '$(pwd)/main/frendy.exe' already exists, skipping compilation..."
fi

echo Adding the following lines to ~/.bashrc:
echo "export FRENDY_PATH=$(pwd)/main/frendy.exe"
echo 'alias frendy="$FRENDY_PATH"'

echo "export FRENDY_PATH=$(pwd)/main/frendy.exe" >> ~/.bashrc
echo 'alias frendy="$FRENDY_PATH"' >> ~/.bashrc

echo -e "\e[32m ✓ Done!\e[0m"