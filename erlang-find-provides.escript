#!/usr/bin/escript
%% -*- erlang -*-

main(EbinFiles) ->
	lists:foreach(
		fun(BeamFile) ->
			try
				{ok, {Module, [{exports,Exports}]}} = beam_lib:chunks(BeamFile, [exports]),
				case Module of
					eunit_test -> io:format ("erlang(eunit_test:nonexisting_function/0)~n");
					wx -> io:format ("erlang(demo:start/0)~n");
					_ -> ok
				end,
				lists:foreach( fun({ModFun,Arity})->io:format("erlang(~p:~s/~p)~n", [Module, ModFun,Arity]) end, Exports)
			catch
				_:_ ->
					ok
			end
		end,
		EbinFiles);

main(_) ->
	halt(1).

