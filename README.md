gitmirrord
==========

`gitmirrord` is a trivial tool that sits and waits for http pings over
localhost on a URL that indicates a repository. When it arrives, it
will push the specified repository to the configured remote, thereby
making it a mirror that's almost live.

When a ping is received the job is put on a queue, and all mirror jobs
are run in the background. A single background thread is used, so only
one repository at a time is being mirrored (if the same repository is
triggered again while a mirror job is still running, it will simply be
pushed once more). Each job has a timeout of 60 seconds for the main
repository and 30 seconds for pushing tags.


Configuration
-------------

Configuration is done using the `gitmirrord.ini` file, where each
repository gets an entry of the form:

```
[repositoryname]
path=/some/where/to/therepo.git
remote=mirror
```

In this case, when a ping is received on `/mirror/repositoryname`
(either with GET or POST), the repository in
`/some/where/to/therepo.git` will be pushed to the remote named
`mirror`.
