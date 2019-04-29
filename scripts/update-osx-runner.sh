set -x
brew install pkg-config || brew upgrade pkg-config
brew install cmake || brew upgrade cmake
brew install pcl || brew upgrade pcl
brew install python3 || brew upgrade python3
brew install pkg-config || brew upgrade pkg-config
brew install homebrew/core/glfw3 || brew upgrade homebrew/core/glfw3
brew install librealsense || brew upgrade librealsense
# Install Deployment repo and dependencies
python3 -m pip install requests mechanize
brew install jpeg-turbo || brew upgrade jpeg-turbo
brew unlink jpeg
brew link --force jpeg-turbo
