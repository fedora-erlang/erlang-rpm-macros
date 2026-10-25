#!/usr/bin/escript
%% -*- erlang -*-

%% SPDX-FileCopyrightText: © 2026 Peter Lemenkov
%% SPDX-FileCopyrightText: erlang-rpm-macros contributors
%% SPDX-License-Identifier: MIT

%% BuildRequires generator for Erlang applications built with rebar3, for
%% %generate_buildrequires. It reads rebar.config in the current directory
%% (and rebar.config.script, the way rebar3 does) and the ones of the
%% applications under apps/, and prints a BuildRequires line for every
%% dependency and build plugin:
%%
%%   (erlang(NAME) or erlang-NAME)
%%
%% Options:
%%   -t           also the dependencies of the test profile
%%   -x NAME,...  skip these dependencies (may be repeated)

main(Args) ->
	{Test, Exclude} = options(Args, false, []),
	Local = [filename:basename(D) || D <- filelib:wildcard("apps/*"), filelib:is_dir(D)],
	Configs = [config(".") | [config(filename:join("apps", A)) || A <- Local]],
	Deps = lists:append([deps(C, Test) || C <- Configs]),
	Skip = Exclude ++ Local,
	Names = lists:usort([N || N <- Deps, not lists:member(N, Skip)]),
	[io:format("(erlang(~s) or erlang-~s)~n", [N, N]) || N <- Names],
	ok.

options([], Test, Exclude) ->
	{Test, Exclude};
options(["-t" | Rest], _Test, Exclude) ->
	options(Rest, true, Exclude);
options(["-x", Names | Rest], Test, Exclude) ->
	options(Rest, Test, Exclude ++ string:lexemes(Names, ", "));
options([Arg | _], _Test, _Exclude) ->
	fail("unknown option ~s", [Arg]).

%% The configuration of the application in Dir, as rebar3 sees it
config(Dir) ->
	File = filename:join(Dir, "rebar.config"),
	Config = case file:consult(File) of
		{ok, Terms} -> Terms;
		{error, enoent} -> [];
		{error, Reason} -> fail("~s: ~s", [File, file:format_error(Reason)])
	end,
	Script = File ++ ".script",
	case filelib:is_regular(Script) of
		true ->
			Bindings = erl_eval:add_binding('CONFIG', Config,
				erl_eval:add_binding('SCRIPT', Script, erl_eval:new_bindings())),
			case file:script(Script, Bindings) of
				{ok, Result} when is_list(Result) -> Result;
				{ok, Other} -> fail("~s: expected a list, got ~p", [Script, Other]);
				{error, Reason2} -> fail("~s: ~s", [Script, file:format_error(Reason2)])
			end;
		false ->
			Config
	end.

%% The names of the dependencies and build plugins in a configuration;
%% project_plugins are development tools and aren't needed to build
deps(Config, Test) ->
	TestDeps = case Test of
		true -> get(deps, get(test, get(profiles, Config)));
		false -> []
	end,
	[N || D <- get(deps, Config) ++ get(plugins, Config) ++ TestDeps, N <- name(D)].

get(Key, Config) when is_list(Config) ->
	case lists:keyfind(Key, 1, Config) of
		{Key, Value} when is_list(Value) -> Value;
		_ -> []
	end;
get(_Key, _Config) ->
	[].

%% A dependency is NAME, or a tuple starting with NAME; raw (non-OTP)
%% dependencies are only source trees and have no application to require
name(Name) when is_atom(Name) -> [atom_to_list(Name)];
name(Name) when is_binary(Name) -> [binary_to_list(Name)];
name(Dep) when is_tuple(Dep), tuple_size(Dep) >= 1 ->
	Opts = element(tuple_size(Dep), Dep),
	case is_list(Opts) andalso lists:member(raw, Opts) of
		true -> [];
		false -> name(element(1, Dep))
	end;
name(_) -> [].

fail(Format, Args) ->
	io:format(standard_error, "erlang-buildrequires: " ++ Format ++ "~n", Args),
	halt(1).
