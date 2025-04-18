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

echo "Until a new FRENDY version is released, one needs to manually change one line in order to fix a bug:"
echo "In 'MGXSUtils/MatxsUtils/MatxsObject.cpp', change the following line:"
echo "  itype_vec.push_back(static_cast<Integer>(hpart.size()));"
echo "to:"
echo "  itype_vec.push_back(static_cast<Integer>(htype.size()));"
echo "The line to change is located at line 1230 of 'MatxsObject.cpp'."
echo "Then, recompile the code using the command './compile_all.csh', as done above."

echo "Actually, the file 'MatxsObject.cpp' should be fetched from the mail from Kenichi Tada, 2025-04-19."
echo "This version contains a fix for the reversed jband and ijj in the 8d card."

echo -e "\e[32m ✓ Done!\e[0m"