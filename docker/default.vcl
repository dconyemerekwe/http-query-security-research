vcl 4.1;

backend default {
    .host = "app";
    .port = "8000";
}

sub vcl_recv {
    if (req.method == "QUERY") {
        return (hash);
    }
}