vcl 4.1;

import std;
import bodyaccess;

backend default {
    .host = "app";
    .port = "8000";
}

sub vcl_recv {
    unset req.http.X-Orig-Method;

    if (req.method == "QUERY") {
        if (!std.cache_req_body(100KB)) {
            return (pass);
        }
        # remember real method; misses are fetched as GET by default
        set req.http.X-Orig-Method = req.method;
        return (hash);
    }
}

# build cache key
sub vcl_hash {
    hash_data(req.method);
    hash_data(req.http.Content-Type);
    hash_data(req.http.Authorization);

    if (req.method == "QUERY") {
        bodyaccess.hash_req_body();
    }
}

# restore QUERY body before sending miss to app
sub vcl_backend_fetch {
    if (bereq.http.X-Orig-Method == "QUERY") {
        set bereq.method = "QUERY";
        unset bereq.http.X-Orig-Method;
    }
}