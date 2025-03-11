# DocMD

Generate a static documentation website from Markdown files in a project's source-code.


## Getting Started

### Install the project

```
cd /path/to/project
git clone git@gitlab.com:webmarka/docmd.git docmd
cd docmd
```

### Customize to your needs

Put your files inside the `src` folder (or customize to your needs).  
Add the `.env` file with your customized params.  
Add `.env.development` and `.env.production` overrides if needed.
You can change the `INCLUDE_PATHS` variable for something outside the 
current directory but currently it works better if the path is inside 
the current directory.  

### Run the setup and start the script all in once : 

```
source ./setup.sh
```

## References

https://gitlab.com/webmarka/docmd
