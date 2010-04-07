#!/usr/bin/escript
%% -*- erlang -*-

main([BeamFile]) ->
	try
		{ok, {_Module, [{imports,Imports}]}} = beam_lib:chunks(BeamFile, [imports]),
		lists:foreach( fun({ModName,ModFun,Arity})->io:format("erlang(~s:~s/~p)~n", [ModName,ModFun,Arity]) end, Imports)
	catch
		_:_ ->
			halt(1)
	end;

main(_) ->
	halt(1).

