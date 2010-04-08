#!/usr/bin/escript
%% -*- erlang -*-

main(EbinFiles) ->
	lists:foreach(
		fun(BeamFile) ->
			try
				{ok, {Module, [{exports,Exports}]}} = beam_lib:chunks(BeamFile, [exports]),
				lists:foreach( fun({ModFun,Arity})->io:format("erlang(~p:~s/~p)~n", [Module, ModFun,Arity]) end, Exports)
			catch
				_:_ ->
					ok
			end
		end,
		EbinFiles);

main(_) ->
	halt(1).

