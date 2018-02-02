FROM fedora

RUN dnf -y install --setopt=install_weak_deps=false --setopt=tsflags=nodocs \
    --setopt=deltarpm=false python2-rpm python3-rpm tox python2-dnf \
    python3-dnf mock && dnf clean all

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

CMD ["/usr/bin/tox"]
