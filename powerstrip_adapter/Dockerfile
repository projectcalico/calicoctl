FROM dockerfile/python

# Install dependencies shared with the master node.  If we can keep this
# in sync then we'll share an FS layer with the master to speed downloads.
RUN apt-get update #&&
RUN apt-get install -qy libffi-dev
RUN apt-get install -qy  libssl-dev
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy in our custom configuration files etc.
COPY root_overlay /

WORKDIR /adapter

# Install Powerstrip Calico Adapter dependencies.
RUN pip install -r requirements.txt

# Listen port for powerstrip adapter.
EXPOSE 2378

# Run the adapter.
CMD ["python", "powerstrip-calico.py"]
