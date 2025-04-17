-module(test).
-export([main/0]).

main() ->
	io:format("HELLO WORLD~n"),
	code:ensure_loaded(crypto),
	application:ensure_started(crypto),
	lists:reverse([0,1,2,3,4]),
	ok.

