#!/usr/bin/env bash
# One-shot bootstrap for a fresh Amazon Linux 2023 / Ubuntu 22.04+ EC2 box.
# Run as ec2-user / ubuntu via SSH:
#
#   curl -fsSL https://raw.githubusercontent.com/<you>/medrag/main/deploy/bootstrap-ec2.sh | bash
#
# Or copy this file up and run it directly.
set -euo pipefail

echo "──> Detecting OS"
. /etc/os-release
OS_ID="${ID:-unknown}"

install_docker_amzn() {
  sudo dnf -y update
  sudo dnf -y install docker git
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$(whoami)"
  # Compose plugin
  DOCKER_CONFIG="${DOCKER_CONFIG:-$HOME/.docker}"
  mkdir -p "$DOCKER_CONFIG/cli-plugins"
  curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
  chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
}

install_docker_ubuntu() {
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg git
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $CODENAME stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$(whoami)"
}

echo "──> Installing Docker for $OS_ID"
case "$OS_ID" in
  amzn)   install_docker_amzn ;;
  ubuntu) install_docker_ubuntu ;;
  *)      echo "Unsupported OS: $OS_ID. Install Docker manually."; exit 1 ;;
esac

echo
echo "✓ Docker installed."
echo "  Log out and back in (or run: newgrp docker) so your user can use docker without sudo."
echo
echo "Next:"
echo "  1. git clone <your repo> medrag && cd medrag"
echo "  2. cp .env.prod.example .env  &&  edit .env"
echo "  3. ./deploy/deploy.sh"
