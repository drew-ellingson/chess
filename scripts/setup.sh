# Setup cutechess

brew install cmake qt6
cd /Users/drew/repos/misc
git clone https://github.com/cutechess/cutechess.git
cd cutechess
cmake -S . -B build
cmake --build build
