#!/usr/bin/escript

# Copyright (c) 2009,2010 Peter Lemenkov <lemenkov@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

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

