# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  # Set up to forward port 5000.
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  config.vm.network "private_network", type: "dhcp"

  # Use NFS to sync folders, because it's faster than VirtualBox sharing.
  config.vm.synced_folder ".", "/vagrant", type: "nfs"
  
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", ENV["MEM"]  || "4096"]
    vb.customize ["modifyvm", :id, "--cpus",   ENV["CPUS"] || "2"]
  end

  config.vm.provision "shell", inline: <<-SHELL
    export COMPOSE_BASE="https://github.com/docker/compose/releases/download"
    export COMPOSE_VERSION="1.3.0"

    echo "### Installing docker"
    wget -qO- https://get.docker.com/ | sh

    echo "### Installing docker-compose"
    curl -sL $COMPOSE_BASE/$COMPOSE_VERSION/docker-compose-`uname -s`-`uname -m` \
      >/usr/local/bin/docker-compose

    chmod +x /usr/local/bin/docker-compose

    echo "### Installing docker-compose bash completion"
    curl -sL https://raw.githubusercontent.com/docker/compose/$COMPOSE_VERSION/contrib/completion/bash/docker-compose \
      >/etc/bash_completion.d/docker-compose

    echo "### Adding vagrant user to docker group"
    usermod -aG docker vagrant

    echo "### Adding resolv.conf DNS fix"
    echo 'options single-request-reopen' >> /etc/resolvconf/resolv.conf.d/tail
    resolvconf -u
  SHELL
end
