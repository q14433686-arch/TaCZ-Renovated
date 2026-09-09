package com.tacz.guns.compat.rei.display;

import com.tacz.guns.crafting.GunSmithTableRecipe;
import com.tacz.guns.crafting.GunSmithTableIngredient;
import me.shedaniel.rei.api.common.category.CategoryIdentifier;
import me.shedaniel.rei.api.common.display.DisplaySerializer;
import me.shedaniel.rei.api.common.display.basic.BasicDisplay;
import me.shedaniel.rei.api.common.entry.EntryIngredient;
import me.shedaniel.rei.api.common.util.EntryIngredients;
import net.minecraft.resources.Identifier;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class GunSmithTableDisplay extends BasicDisplay {
    private final GunSmithTableRecipe recipe;
    private final Map.Entry<Identifier, CategoryIdentifier<GunSmithTableDisplay>> entry;

    public GunSmithTableDisplay(GunSmithTableRecipe recipe, Map.Entry<Identifier, CategoryIdentifier<GunSmithTableDisplay>> entry) {
        super(toEntryIngredients(recipe), Collections.singletonList(EntryIngredients.of(recipe.getOutput())),
                Optional.ofNullable(entry.getKey()));
        this.recipe = recipe;
        this.entry = entry;
    }

    /**
     * Keep one REI input slot for each gun-smith material. A material can legitimately still be
     * unresolved after the registration-time resolve attempt (for example, a bad third-party tag),
     * so represent it as an empty entry rather than passing null to REI's ingredient converter.
     */
    private static List<EntryIngredient> toEntryIngredients(GunSmithTableRecipe recipe) {
        List<GunSmithTableIngredient> inputs = recipe.getInputs();
        if (inputs == null || inputs.isEmpty()) {
            return List.of();
        }
        return inputs.stream()
                .map(input -> {
                    if (input == null) {
                        return EntryIngredient.empty();
                    }
                    var resolved = input.getIngredient();
                    return resolved == null ? EntryIngredient.empty() : EntryIngredients.ofIngredient(resolved);
                })
                .toList();
    }

    public GunSmithTableRecipe getRecipe() {
        return recipe;
    }

    @Override
    public CategoryIdentifier<?> getCategoryIdentifier() {
        return entry.getValue();
    }


    @Override
    public DisplaySerializer<? extends GunSmithTableDisplay> getSerializer() {
        return null;
    }
}
