#!/usr/bin/escript
%% -*- erlang -*-

main([BeamFile]) ->
	try
		{ok, {Module, [{exports,Exports}]}} = beam_lib:chunks(BeamFile, [exports]),
		lists:foreach( fun({ModFun,Arity})->io:format("erlang(~p:~s/~p)~n", [Module, ModFun,Arity]) end, Exports)
	catch
		_:_ ->
			halt(1)
	end;

main(_) ->
	halt(1).

