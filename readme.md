**A simple Python code for interacting with Minecraft Java Edition save files.**
<br>
<ul>
<li>Provides easy reading and saving of Java's primitive data types (java_data_io.py)</li>
<li>Completely supports I/O on the latest revision of Named Binary Tag (NBT) format (nbt_lib.py)</li>
<li>Interacts with both uncompressed and compressed files</li>
<li>Implementation of McRegion chunk data storage container, ported from Java language (region_file.py)</li>
<li>Supports gzip and zlib compression</li>
<li>Example program for optimizing an older SkyBlock type map (skyblock_optimizer.py), using above I/O hooks.</li>
</ul>
<br>
Original Java code used for reference: <br>
<a href="https://assets.minecraft.net/12w07a/Minecraft.AnvilConverter.zip">https://assets.minecraft.net/12w07a/Minecraft.AnvilConverter.zip</a>