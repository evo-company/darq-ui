# /bin/env bash

set -e
USAGE="Usage: release.sh 0.1.1 'Release message'"

VERSION=$1
MESSAGE=$2

if [ -z "${VERSION}" ]; then
  echo $USAGE
  echo "VERSION is not set"
  exit 1
fi
if [ -z "${MESSAGE}" ]; then
  echo $USAGE
  echo "MESSAGE is not set"
  exit 1
fi
echo "* Releasing version ${VERSION}"

VERSION_FILE="src/darq_ui/__init__.py"

echo "__version__ = \"${VERSION}\"" >${VERSION_FILE}
git add src/darq_ui/__init__.py
echo "* Commiting new version ${VERSION}" to ${VERSION_FILE}
git commit -m "Release ${VERSION}"
echo "* Creating new tag ${VERSION}"
git tag -a v${VERSION} -m "${MESSAGE}"
echo "* Pushing tag ${VERSION}"
git push origin main --tags
