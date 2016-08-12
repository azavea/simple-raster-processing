# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.8"

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  # config.vm.synced_folder "~/.aws", "/home/vagrant/.aws"

  config.vm.provider :virtualbox do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end

  # Geop Gunicorn
  config.vm.network :forwarded_port, guest: 8080, host: 8080

  # Geop Flask debug server
  config.vm.network :forwarded_port, guest: 8081, host: 8081

  # Sync a data directory which contains rasters on the host
  config.vm.synced_folder ENV['DATA_DIR'], "/vagrant/data"

  # Change working directory to /vagrant upon session start.
  config.vm.provision "shell", inline: <<SCRIPT
    if ! grep -q "cd /vagrant" "/home/vagrant/.bashrc"; then
        echo "cd /vagrant" >> "/home/vagrant/.bashrc"
    fi
SCRIPT

  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "deployment/ansible/simple-raster-processing.yml"
      ansible.galaxy_role_file = "deployment/ansible/roles.yml"
  end
end
