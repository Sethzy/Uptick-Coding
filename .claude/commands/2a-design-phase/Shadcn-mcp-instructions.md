##step 1

Could you use the Shadcn demo tool for any component, and tell me how it was used?

Get-component-demo: shows you the real code, and how it's meant to be implemented.

Get-block: is a combination of componenets used together.

##step 2

"mcp-store.md

"@shad-cn.mdc"

"Please look at the @mcp-store.md and make an ui-implementation using shadcn ui as to what components will be used in the ui structure and where. And you should only write the name of the appropriate components to be used. Not the code."

##step 3

@shad-cn.mdc Implement this @implementation.md inside
@/shadcn-app .

ShadCN in installed.

Now, if we look at what's actually being built right now, you'll see that I referenced the rule file again and told cursor to implement this plan inside the Shad CN app. As the system works through the process, it's adding all the components step by step, building everything methodically.
Here's what's fascinating. Once it finishes with a specific set of blocks and components, it calls the tools again. And this happens because that's exactly how it's programmed in the rule file. Because of that programming, it never strays from the process. It consistently fetches the context first. And this is the crucial part we've been exploring with context engineering.

##Step 4

Go to TweakCN, copy the command and give it to cursor to install.

Eg. pnpm etc.

Then, give cursor the code to modify the theme directly.
