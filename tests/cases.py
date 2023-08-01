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
	
	
	if a == 3 then
		func2()
	elseif a == 4 then
		func3()
	elseif a == 5 then
		func4()
	elseif a == 6 then
		func5()
	elseif a == 7 then
		func6()
	end
 
	if y == z then
		func7()
	end
 
	local a = x + y
	await(foo())
	await(foo())
	bar()
	await(foo())
	
 	if x == z then
		await(func4())
	end
 
	local b = a + 1
end
 
"""

source_code_7 = """
function exerciseLuaFeatures()
    -- Declare local and global variables
    local localVar = 5
    _G.globalVar = 10

    -- Loops
    for i=1, 10 do
        localVar = localVar + i
    end

    while localVar < 100 do
        localVar = localVar + 10
    end
    
    repeat
        localVar = localVar - 10
    until localVar <= 50

    -- Conditional statements
    if localVar == 50 then
        localVar = localVar * 2
    elseif localVar < 50 then
        localVar = localVar + 50
    else
        localVar = localVar - 50
    end

    -- Table
    local tbl = {1, 2, 3, localVar, globalVar, "test"}

    -- Access table
    local x = tbl[5]

    -- Metatable
    local meta = { __index = tbl }

    -- Set metatable
    setmetatable(tbl, meta)

    -- More table
    local moreTbl = { localVar = localVar, globalVar = _G.globalVar, status = status }

    -- Table iteration
    for key, value in pairs(moreTbl) do
        print(key .. ": " .. tostring(value))
    end

    -- Return values
    return localVar, _G.globalVar, sum
end

"""

source_code_8 = """
function mine_resource(ore_type, quantity)
    -- Check if arguments are valid
    if type(ore_type) ~= 'string' or type(quantity) ~= 'number' then
        clog("Invalid arguments. 'ore_type' should be a string and 'quantity' should be a number.")
        return false
    end

  
    -- Check if the ore type exists
    -- if not resource then
    --     clog("No resource of type " .. ore_type .. " found.")
    --     return false
    -- end

    local player = game.players[1]

    -- Check if the player is in a valid state
    if not player.character or player.character.mining_state.mining then
        clog("Player is not in a valid state for mining.")
        return false
    end

    -- Find nearest ore entity
    local position = player.character.position
    local surface = player.surface
    local entity = find_nearest_ore(surface, position, ore_type)

    -- Move to ore position
    move(entity.position)

    -- Mining ore
    for i=1,quantity do
        await(mine(entity))
    end

    -- If the mining process was successful, return true
    return true
end

return mine_resource
"""