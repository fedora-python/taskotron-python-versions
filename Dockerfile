FROM fedora

RUN dnf -y install --setopt=install_weak_deps=false --setopt=tsflags=nodocs \
    --setopt=deltarpm=false python2-rpm libtaskotron-core libtaskotron-fedora \
    python3-rpm tox python2 python3 python2-dnf python3-dnf \
    python2-libarchive-c && dnf clean all

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

CMD ["/usr/bin/tox"]
