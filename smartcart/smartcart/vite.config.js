import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],

  build: {
    /* Vite empties `dist` before every build. On this machine that
       step is what fails: the deletion is routed through a trash
       helper that times out, so the build dies with
       "[safe-delete] ... ETIMEDOUT" AFTER all modules have already
       transformed successfully.

       Turning it off makes the build work. Vite overwrites the files
       it emits, and the only cost is that a stale file from a
       previous build could linger if its name changed. The output
       filenames are content-hashed (index-B_0iUgCL.js), so a rename
       always produces a new name.

       If stale assets ever do accumulate, delete `dist` by hand
       before building. */
    emptyOutDir: false,
  },
})