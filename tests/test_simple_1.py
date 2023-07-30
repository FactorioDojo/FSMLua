

source_lua_code = \
"""
foo()
bar()
foo()
"""

target_lua_code = \
"""

"""


# Given Lua source code
source_code_1 = """
function doThing()
		bar()
		await(foo())
		bar()
end
"""

source_code_2 = """
function doThing()
		local value = bar()
		if value == 1 then
  			await(foo())
		else
			bar()
		end
		bar()
end
"""

source_code_3 = """
function doThing()
		local value = bar()
		if value == 1 then
  			await(foo())
		end
  		bar()
		local x = 2
		doThing()
		if value == 2 then
			value = 3
		else
			value = 4
		end
end
"""

source_code_4 = """
function doThing()
	local var = bar()
	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
		end
		bar()
	else
		car()
	end
	bar()
 	if var == thing1 then
		await(foo()) 
	end
	car()
end
"""


source_code_5 = """
function doThing()
	local var = bar()
	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
			doThing()
			local x = 3
			await(foo())
			doOtherThing()
		end
		bar()
	else
		car()
	end
	bar() 
 	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
		end
		bar()
	else
		car()
	end
	bar()
 
end
"""

source_code_6 = """
function doThing()
	local x = 1
	local y = 2
	local z = 3
	
	if x == y then
		await(func1())
		y = func2()
	end
	
	local a = x + y
	
	if a == 3 then
		func2()
	elseif a == 4 then
		func3()
	end
 
	if x == z then
		await(func4())
	end
 
	local b = a + 1
end
 
"""